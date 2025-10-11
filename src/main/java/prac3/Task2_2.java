package prac3;

import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Observable;

import java.util.Random;
import java.util.concurrent.TimeUnit;

public class Task2_2 {
    record File(
            int size
    ) {}
    public static void main(String[] args) {
        third();
    }

    private static void first() {
        Observable.range(0, 1000)
                .map((value) ->  new Random().nextInt(0, 1000))
                .filter((value) -> value > 500)
                .blockingSubscribe(System.out::println);
    }

    private static void second() {
        var flow1 = Observable.range(0, 1000).map((value) -> "From flow 1 " + value)
                .delay(1000, TimeUnit.MILLISECONDS);
        var flow2 = Observable.range(0, 1000).map((value) -> "From flow 2 " + value);

        Observable.concat(flow1, flow2)
                .blockingSubscribe(System.out::println);
    }

    private static void third() {
        Observable.range(0, 10).map((value) -> new Random().nextInt(0, 1000))
                .take(5)
                .blockingSubscribe(System.out::println);
    }
}
